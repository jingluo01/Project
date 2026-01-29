# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
# COPY nginx.conf /etc/nginx/conf.d/default.conf # 后面我们可以添加自定义nginx配置

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
