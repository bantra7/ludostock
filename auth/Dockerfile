FROM node:20-alpine AS build

WORKDIR /app/auth

COPY auth/package*.json ./
RUN npm install

COPY auth ./
RUN npm run build

FROM node:20-alpine

WORKDIR /app/auth

COPY --from=build /app/auth/dist ./dist
COPY --from=build /app/auth/node_modules ./node_modules
COPY auth/package.json ./

EXPOSE 3001

CMD ["npm", "run", "start"]
