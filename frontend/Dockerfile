# Stage 1: Build the React application
FROM node:18 AS build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
COPY VERSION /app/VERSION
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:alpine

COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
