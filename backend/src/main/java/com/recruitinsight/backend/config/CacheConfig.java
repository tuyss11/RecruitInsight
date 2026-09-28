package com.recruitinsight.backend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.Cache;
import org.springframework.cache.annotation.CachingConfigurer;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.interceptor.CacheErrorHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.serializer.GenericJacksonJsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import tools.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import tools.jackson.databind.jsontype.PolymorphicTypeValidator;

import java.time.Duration;

@Configuration
@EnableCaching
public class CacheConfig implements CachingConfigurer {

    public static final Duration STATISTICS_TTL = Duration.ofMinutes(10);

    @Bean
    public RedisCacheConfiguration redisCacheConfiguration() {
        PolymorphicTypeValidator typeValidator = BasicPolymorphicTypeValidator.builder()
                .allowIfSubType("com.recruitinsight.backend.dto.statistics")
                .allowIfSubType("java.util")
                .allowIfSubType("java.math")
                .build();
        GenericJacksonJsonRedisSerializer valueSerializer =
                GenericJacksonJsonRedisSerializer.builder()
                        .enableDefaultTyping(typeValidator)
                        .build();

        return RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(STATISTICS_TTL)
                .disableCachingNullValues()
                .computePrefixWith(cacheName -> cacheName + ":")
                .serializeKeysWith(RedisSerializationContext.SerializationPair
                        .fromSerializer(new StringRedisSerializer()))
                .serializeValuesWith(RedisSerializationContext.SerializationPair
                        .fromSerializer(valueSerializer));
    }

    @Override
    public CacheErrorHandler errorHandler() {
        return new LoggingCacheErrorHandler();
    }

    private static final class LoggingCacheErrorHandler implements CacheErrorHandler {

        private static final Logger LOGGER = LoggerFactory.getLogger(LoggingCacheErrorHandler.class);

        @Override
        public void handleCacheGetError(RuntimeException exception, Cache cache, Object key) {
            log("read", exception, cache, key);
        }

        @Override
        public void handleCachePutError(
                RuntimeException exception,
                Cache cache,
                Object key,
                Object value
        ) {
            log("write", exception, cache, key);
        }

        @Override
        public void handleCacheEvictError(RuntimeException exception, Cache cache, Object key) {
            log("evict", exception, cache, key);
        }

        @Override
        public void handleCacheClearError(RuntimeException exception, Cache cache) {
            log("clear", exception, cache, "all");
        }

        private void log(String operation, RuntimeException exception, Cache cache, Object key) {
            LOGGER.warn(
                    "Redis cache {} failed for cache={} key={}; continuing without cache",
                    operation,
                    cache.getName(),
                    key,
                    exception
            );
        }
    }
}
