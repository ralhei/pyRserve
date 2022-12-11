FROM alpine:latest

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

ENV R_VERSION 4.2.2
ENV R_SOURCE /usr/src

ENV BUILD_DEPS \
    wget \
    perl \
    tar

ENV PERSISTENT_DEPS \
    gcc \
    g++ \
    gfortran \
    icu-dev \
    libjpeg-turbo \
    libpng-dev \
    make \
    openblas-dev \
    pcre2-dev  \
    readline-dev \
    xz-dev \
    zlib-dev \
    bzip2-dev \
    curl-dev

RUN apk upgrade --update && \
    apk add --no-cache --virtual .build-deps $BUILD_DEPS && \
    apk add --no-cache --virtual .persistent-deps $PERSISTENT_DEPS
RUN mkdir -p $R_SOURCE && cd $R_SOURCE && \
    wget https://cran.r-project.org/src/base/R-4/R-${R_VERSION}.tar.gz && \
    tar -xf R-${R_VERSION}.tar.gz && \
    cd R-${R_VERSION} && \
    ./configure --prefix=/usr/local --without-x --enable-R-shlib && \
    make && make install && \
    wget https://www.rforge.net/Rserve/snapshot/Rserve_1.8-12.tar.gz && \
    PKG_CPPFLAGS=-DNODAEMON  R CMD INSTALL Rserve_1.8-12.tar.gz && \
    apk del .build-deps && \
    cd / && \
    rm -rf $R_SOURCE
RUN echo -e "remote enable\noob enable\neval library(Rserve)" > /etc/Rserv.conf

CMD ["R", "CMD", "Rserve"]
