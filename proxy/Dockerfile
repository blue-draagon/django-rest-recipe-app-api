FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="khalifaasene10@mail.com"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

USER root

RUN mkdir -p /volumes/static
RUN chmod 755 /volumes/static
RUN touch /etc/nginx/conf.d/default.conf
RUN chown nginx:nginx /etc/nginx/conf.d/default.conf
RUN chmod +x /run.sh

VOLUME /volumes/static

USER nginx

CMD [ "/run.sh" ]