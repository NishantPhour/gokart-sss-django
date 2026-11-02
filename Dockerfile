# Prepare the base environment.
FROM ghcr.io/dbca-wa/docker-apps-dev:ubuntu_2604_base_python AS builder_base_govapp
LABEL org.opencontainers.image.authors=asi@dbca.wa.gov.au
LABEL org.opencontainers.image.source=https://github.com/dbca-wa/gokart-sss-django
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
#ENV DEBUG=True
ENV TZ=Australia/Perth
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV NOTIFICATION_EMAIL='no-reply@dbca.wa.gov.au'
ENV NON_PROD_EMAIL='none@none.com'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_DOMAIN='dbca.wa.gov.au'

RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
# RUN apt-get install --no-install-recommends -y curl wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata cron rsyslog gunicorn
# RUN apt-get install --no-install-recommends -y libpq-dev patch libreoffice virtualenv
# RUN apt-get install --no-install-recommends -y postgresql-client mtr htop vim  sudo
RUN apt-get install --no-install-recommends -y bzip2 pdftk unzip
# RUN apt-get install --no-install-recommends -y software-properties-common
# RUN apt-get install --no-install-recommends -y run-one
# RUN ln -s /usr/bin/python3 /usr/bin/python

# Install GDAL
# RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
# RUN apt update
# RUN apt-get install --no-install-recommends -y gdal-bin python3-gdal
# RUN apt-get install --no-install-recommends -y libgdal-dev build-essential


# Install nodejs
RUN update-ca-certificates

WORKDIR /app

# install node 16
RUN touch install_node.sh
RUN curl -fsSL https://deb.nodesource.com/setup_18.x -o install_node.sh
RUN chmod +x install_node.sh && ./install_node.sh
RUN apt-get update
RUN apt-get install -y nodejs
RUN apt-get install -y uglifyjs
RUN npm install -g browserify
RUN npm install -g npm-run-all
RUN npm install -g closure-util

# Install nodejs
COPY python-cron python-cron
COPY startup.sh pre_startup.sh /
COPY ./timezone /etc/timezone
COPY sss sss
COPY packages packages
RUN chmod 755 /startup.sh && \
    chmod +s /startup.sh && \
    chmod 755 /pre_startup.sh && \
    chmod +s /pre_startup.sh && \
    groupadd -g 5000 oim && \
    useradd -g 5000 -u 5000 oim -s /bin/bash -d /app && \    
    chown -R oim.oim /app && \
    mkdir /container-config/ && \
    chown -R oim.oim /container-config/ && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    touch /app/rand_hash

# Default Scripts
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
RUN chmod 755 /tmp/default_script_installer.sh
RUN /tmp/default_script_installer.sh

RUN chmod 755 /pre_startup.sh
# Install Python libs from requirements.txt.
FROM builder_base_govapp AS python_libs_govapp

USER oim
ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV

ENV PATH=/app/venv/bin:$PATH



RUN whereis python
COPY --chown=oim:oim requirements.txt ./
COPY --chown=oim:oim src src
COPY --chown=oim:oim .git .git
COPY --chown=oim:oim package.json ./
# COPY --chown=oim:oim package-lock.json ./
COPY --chown=oim:oim profile.py ./
RUN pip install --upgrade pip
RUN uv pip install -r requirements.txt
RUN pip install npm
#\ && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

RUN npm install --loglevel verbose
RUN npm run build

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_govapp
COPY --chown=oim:oim gunicorn.ini manage.py uwsgi_prod.ini ./
RUN touch /app/.env

RUN python manage.py collectstatic --noinput

RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

# IPYTHONDIR - Will allow shell_plus (in Docker) to remember history between sessions
# 1. will create dir, if it does not already exist
# 2. will create profile, if it does not already exist
#RUN mkdir /app/logs/.ipython
#RUN export IPYTHONDIR=/app/logs/.ipython/
# Cleanup
USER root
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/refs/heads/main/wagov_utils/bin/package_cleanup_2604.sh -O /tmp/package_cleanup_2604.sh
RUN chmod 755 /tmp/package_cleanup_2604.sh
RUN /tmp/package_cleanup_2604.sh
USER oim

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/bin/bash", "-c", "/startup.sh"]
