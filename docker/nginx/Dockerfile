FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

COPY default.conf.template /etc/nginx/templates/default.conf.template

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
