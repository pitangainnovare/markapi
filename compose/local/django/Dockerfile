ARG PYTHON_VERSION=3.11-bullseye

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  git \
  # psycopg2 dependencies
  libpq-dev \
  # other dependencies
  software-properties-common \
  libopenblas-dev \
  libomp-dev

# Instalar gcc-10 y g++-10 en Debian Bullseye
RUN apt-get update && \
    apt-get install -y gcc-10 g++-10 ninja-build cmake && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 50 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 50 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar ninja-build y cmake
RUN apt-get install -y ninja-build cmake

# Configurar variables de entorno para compilar con BLAS y SIMD condicionalmente
ARG ENABLE_OPTIMIZATIONS=true
RUN if [ "${ENABLE_OPTIMIZATIONS}" = "true" ]; then \
  export CFLAGS="-mfma -mavx2"; \
  export CXXFLAGS="-mfma -mavx2"; \
  export CMAKE_ARGS="-DGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"; \
  fi

# Actualizar pip, setuptools y wheel antes de instalar dependencias
RUN python -m pip install --upgrade pip setuptools wheel

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Update pip
RUN python -m pip install --upgrade pip

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
  -r ${BUILD_ENVIRONMENT}.txt

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

# Disable AVX support for llama-cpp-python if needed
ARG DISABLE_AVX=false

# Set the version of llama-cpp-python
ARG LLAMA_VERSION=0.3.14

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# Use wheels to install python dependencies (excluding llama-cpp-python)
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ $(find /wheels/ -name "*.whl" ! -name "llama_cpp_python*") \
	&& rm -rf /wheels/

# Install llama-cpp-python with specific CMAKE flags for Kubernetes nodes with or without AVX support
RUN if [ "${DISABLE_AVX}" = "true" ]; then \
  CMAKE_ARGS='-DLLAMA_AVX=OFF -DLLAMA_AVX2=OFF -DLLAMA_FMA=OFF -DLLAMA_F16C=OFF -DLLAMA_OPENMP=ON' pip install llama-cpp-python==${LLAMA_VERSION} --force-reinstall --no-cache-dir; \
    else \
  pip install llama-cpp-python==${LLAMA_VERSION} --force-reinstall --no-cache-dir; \
    fi

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

# copy application code to WORKDIR
COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint"]
