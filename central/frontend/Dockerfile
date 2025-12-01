FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

ENV REACT_APP_COMMAND_SERVICE_URL=http://localhost:5000
ENV REACT_APP_BOOKING_SERVICE_URL=http://localhost:3003
ENV REACT_APP_GRAFANA_URL=http://localhost:3000

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
