# ----------------------------
# Build stage
# ----------------------------
FROM node:18.18.1-alpine3.18 AS build

WORKDIR /app

RUN apk add --no-cache python3 make g++

ENV PATH=/app/node_modules/.bin:$PATH

ENV REACT_APP_GRAFANA_URL=/grafana
ENV REACT_APP_COMMAND_SERVICE_URL=/api/command
ENV REACT_APP_BOOKING_SERVICE_URL=/api/booking

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build


FROM nginx:1.23-alpine

COPY --from=build /app/build /usr/share/nginx/html

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
