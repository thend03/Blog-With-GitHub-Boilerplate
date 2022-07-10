---
layout: post
title: junit下测试用例使用线程池问题
slug: junit-multi-thread-problem
date: 2022-05-30 21:12
status: publish
author: thend03
categories:
  - 默认分类
tags:
  - junit
  - multi thread

excerpt: junit测试用例使用线程池问题
---



## 问题起因

有一次要测试下多线程删除redis数据，会不会有问题，比如边界条件没控制好啥的，导致多删数据了，我就想着写一个测试用例，使用线程池去模拟多线程删除的场景。

原以为是个很简单的场景，结果多线程咋整都有问题。

下面上个对比的代码，单线程和多线程访问执行，以redis查询为例。



```java
import com.google.common.util.concurrent.ThreadFactoryBuilder;
import com.zto.titans.zim.service.ServiceApplication;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Objects;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = ServiceApplication.class)
public class BigKeysTest {
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    private final String key = "test_set_add_4";

    private final ThreadPoolExecutor CLEAN_TASK_EXECUTOR = new ThreadPoolExecutor(2, 4, 60, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(10), new ThreadFactoryBuilder().setNameFormat("sorted-set-clean-task-%d").build());
  
  
  @Test
    public void testCard() {
        Long count = redisTemplate.opsForZSet().zCard(key);
        System.out.println(count);
    }


    @Test
    public void multiCard() throws InterruptedException {
        for (int i = 0; i < 2; i++) {
            CLEAN_TASK_EXECUTOR.execute(() -> {
                try {
                    Long countOfZset = redisTemplate.opsForZSet().zCard(key);
                    System.out.println(countOfZset);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
        System.out.println("end");
    }

    @Test
    public void testAddAndGet() {
        redisTemplate.opsForZSet().zCard(key);
        
    }
}
```



分别执行testCard()和multiCard2个用例，会发现testCard会顺利打印zset key的元素数量，而multiCard只会打印一个end，也不会打印数量，也没有任何报错。

![image-20220710113010666](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101130699.png)



断点执行，可以获取到错误

![image-20220710113131178](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101131201.png)



上面是我写这篇文章时，debug获得的错误，我第一次遇到的错误信息是这个,无法从连接池获取连接，给我一顿折磨

```
org.springframework.data.redis.connection.PoolException: Could not get a resource from the pool; nested exception is io.lettuce.core.RedisException: Cannot retrieve initial cluster partitions from initial URIs [RedisURI [host='10.7.100.100', port=6381], RedisURI [host='10.7.100.101', port=6381], RedisURI [host='10.7.100.101', port=6382], RedisURI [host='10.7.100.100', port=6382]]
```





## 问题分析

一开始我以为是我的redis cluster出现了问题，但是试了好几次testCard()方法都没问题，后来我就去搜了一下，然后发现junit执行完会执行直接退出，而不是等到所有线程都执行完才会退出

再来复习下jvm退出的条件，一般有2个条件

- jvm中的所有线程都是守护线程
- 调用System.exit()执行退出

junit就是在main方法执行完之后调用了System.exit()直接退出了，而不会等待子线程执行完毕

![image-20220710151758587](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101517610.png)

## 解决方法

解决方法有几种，核心目的都是为了让main线程等子线程执行完再退出，有下面几种方法

- Thread.sleep(1000)，让main线程睡一会，子线程得以执行
- Thread.join()，不过join的话不能用线程池，自己new Thread()，获取线程的引用
- 使用CountDownLatch，等子线程执行完了再去执行main线程

关于Thread.join()，由于我是用的线程池，没有手动new Thread()，不知道线程池有没有办法做join，有知道的可以评论区告诉我一下。

我是用的CountDownLatch，给一下我的CountDownLatch的示例

```java
@Test
public void multiCard() {
        CountDownLatch countDownLatch = new CountDownLatch(2);
        for (int i = 0; i < 2; i++) {
            CLEAN_TASK_EXECUTOR.execute(() -> {
                try {
                    Long countOfZset = redisTemplate.opsForZSet().zCard(key);
                    System.out.println("zset count: " + countOfZset);
                    countDownLatch.countDown();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
        try {
            countDownLatch.await(5, TimeUnit.SECONDS);
            System.out.println("count down end");
        } catch (InterruptedException e) {
            //ignore
        }
        System.out.println("end");
}
```

看控制台输出，2个子线程正常执行完了

![image-20220710154259740](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101542769.png)



## 号外

我第一次遇到这个问题的时候，当天就根据junit+多线程搜到了原因，就是junit的main方法执行完会退出。

我出于好奇，又跟了一下，想看看哪个地方执行的退出的，上面贴过的这张图，debug的时候根本就没走这里

![image-20220710151758587](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101517610.png)



下面分享下我在找test执行流程的过程。

我这个是一个SpringBoot工程，然后每个测试类都会用打上下面2个注解

```
@RunWith(SpringRunner.class)
@SpringBootTest(classes = ServiceApplication.class)
```

然后我先找到了这个断点位置`org.springframework.test.context.junit4.SpringJUnit4ClassRunner#run`

![image-20220710155256627](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101552654.png)



然后顺着这个方法往上找，上层调用位置是`org.junit.runner.JUnitCore#run(org.junit.runner.Runner)`

![image-20220710155438424](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101554446.png)

但是顺着JUnitCore#run往上找调用的时候，发现上层调用的2个地方断点根本都不会进

![image-20220710155816570](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101558598.png)



然后我在debug的时候，发现有一个往前的按钮，点击这个按钮就可以回到最最开始的入口

![](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101613001.mov)

就是这个类com.intellij.rt.junit.JUnitStarter，但是我在idea里没有看到相关的源码。

后来我又搜了一下，在github上搜到了一个类文件，这个类文件的main方法最后也是执行了System.exit()

![image-20220710161335317](https://cdn.jsdelivr.net/gh/thend03/mdPic/picGo/202207101613352.png)



[github类文件地址](https://github.com/joewalnes/idea-community/blob/master/plugins/junit_rt/src/com/intellij/rt/execution/junit/JUnitStarter.java)

这个可能是idea自己对junit做了封装，更多的细节我暂时没有探索到，有知道的也可以评论区告诉我



## 后记

总的来说，这是个说大不大，说小不小的问题，如果对junit和jvm的退出机制了解不是很多的情况下，可能会和我犯一样的错误，浪费几个小时的时间在那debug。

我debug的过程中，甚至debug到了netty的worker关闭的代码，我甚至都在怀疑，netty出问题了???

后来实际证明是我自己想多了。

不过也不能说踩坑不好吧，生活总是在趟过一个又一个或大或小的坑中过去的。

希望大家都能将遇到的每一个坑和挫折踩在脚下，快乐成长

