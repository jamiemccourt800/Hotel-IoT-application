# build stage
FROM node:18-alpine AS build
WORKDIR /app

# install build dependencies
RUN apk add --no-cache python3 make g++

# set environment variables for build
ENV REACT_APP_HOTELID=hotel_01
ENV REACT_APP_ROOMID=101
ENV REACT_APP_COMMAND_SERVICE_URL=/command

ENV PATH=/app/node_modules/.bin:$PATH

# install dependencies
COPY package*.json ./
RUN npm install --silent
RUN npm install react-scripts@5.0.1 -g --silent

# copy source and build
COPY . /app
RUN npm run build

# production stage
FROM nginx:1.23-alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]