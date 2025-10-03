import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Box, Fade } from '@mui/material';
import { LoadingSpinner, DashboardSkeleton } from './index';

// Higher-order component for lazy loading with enhanced UX
export const withLazyLoading = (
  importFunc, 
  fallbackComponent = null,
  options = {}
) => {
  const {
    delay = 200, // Minimum loading time to prevent flash
    skeleton = false,
    variant = 'discord'
  } = options;

  const LazyComponent = lazy(importFunc);

  return React.forwardRef((props, ref) => {
    const [showFallback, setShowFallback] = useState(true);
    const [minDelayPassed, setMinDelayPassed] = useState(false);

    useEffect(() => {
      const timer = setTimeout(() => {
        setMinDelayPassed(true);
      }, delay);

      return () => clearTimeout(timer);
    }, [delay]);

    const handleComponentLoad = () => {
      if (minDelayPassed) {
        setShowFallback(false);
      }
    };

    const FallbackComponent = fallbackComponent || (
      skeleton ? (
        <DashboardSkeleton />
      ) : (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '200px',
            width: '100%',
          }}
        >
          <LoadingSpinner 
            variant={variant}
            size={40}
            message="Loading component..."
          />
        </Box>
      )
    );

    return (
      <Suspense fallback={FallbackComponent}>
        <Fade in={!showFallback} timeout={300}>
          <Box>
            <LazyComponent 
              {...props} 
              ref={ref}
              onLoad={handleComponentLoad}
            />
          </Box>
        </Fade>
      </Suspense>
    );
  });
};

// Intersection Observer based lazy loading for images and content
export const LazyImage = ({ 
  src, 
  alt, 
  placeholder, 
  className,
  style,
  onLoad,
  ...props 
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [imgRef, setImgRef] = useState(null);

  useEffect(() => {
    if (!imgRef) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
      }
    );

    observer.observe(imgRef);

    return () => observer.disconnect();
  }, [imgRef]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  return (
    <Box
      ref={setImgRef}
      sx={{
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: 'grey.100',
        ...style,
      }}
      className={className}
      {...props}
    >
      {/* Placeholder */}
      {!isLoaded && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'grey.200',
          }}
        >
          {placeholder || (
            <LoadingSpinner size={24} variant="discord" />
          )}
        </Box>
      )}
      
      {/* Actual image */}
      {isInView && (
        <Fade in={isLoaded} timeout={300}>
          <Box
            component="img"
            src={src}
            alt={alt}
            onLoad={handleLoad}
            sx={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: isLoaded ? 'block' : 'none',
            }}
          />
        </Fade>
      )}
    </Box>
  );
};

// Lazy content loader with intersection observer
export const LazyContent = ({ 
  children, 
  fallback, 
  threshold = 0.1, 
  rootMargin = '50px',
  once = true 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [elementRef, setElementRef] = useState(null);

  useEffect(() => {
    if (!elementRef) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          if (once) {
            observer.disconnect();
          }
        } else if (!once) {
          setIsVisible(false);
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    observer.observe(elementRef);

    return () => observer.disconnect();
  }, [elementRef, threshold, rootMargin, once]);

  return (
    <Box ref={setElementRef}>
      {isVisible ? (
        <Fade in={isVisible} timeout={300}>
          <Box>{children}</Box>
        </Fade>
      ) : (
        fallback || (
          <Box
            sx={{
              minHeight: '100px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <LoadingSpinner size={24} variant="discord" />
          </Box>
        )
      )}
    </Box>
  );
};

// Virtual scrolling for large lists
export const VirtualList = ({ 
  items, 
  renderItem, 
  itemHeight = 60,
  containerHeight = 400,
  overscan = 5 
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerRef, setContainerRef] = useState(null);

  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight) + overscan,
    items.length
  );

  const visibleItems = items.slice(
    Math.max(0, visibleStart - overscan),
    visibleEnd
  );

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };

  return (
    <Box
      ref={setContainerRef}
      onScroll={handleScroll}
      sx={{
        height: containerHeight,
        overflow: 'auto',
        position: 'relative',
      }}
    >
      {/* Total height spacer */}
      <Box sx={{ height: items.length * itemHeight, position: 'relative' }}>
        {/* Visible items */}
        {visibleItems.map((item, index) => {
          const actualIndex = Math.max(0, visibleStart - overscan) + index;
          return (
            <Box
              key={actualIndex}
              sx={{
                position: 'absolute',
                top: actualIndex * itemHeight,
                left: 0,
                right: 0,
                height: itemHeight,
              }}
            >
              {renderItem(item, actualIndex)}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

// Preload component for critical resources
export const PreloadResource = ({ href, as = 'script', onLoad, onError }) => {
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    
    if (onLoad) link.onload = onLoad;
    if (onError) link.onerror = onError;
    
    document.head.appendChild(link);
    
    return () => {
      if (document.head.contains(link)) {
        document.head.removeChild(link);
      }
    };
  }, [href, as, onLoad, onError]);

  return null;
};

export default {
  withLazyLoading,
  LazyImage,
  LazyContent,
  VirtualList,
  PreloadResource,
};