# Build the app
FROM node:20-alpine AS builder

WORKDIR /app

COPY ./project .

RUN npm install

RUN npm run build

# Run the app
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/package.json /app/package-lock.json* ./
RUN npm install --production

COPY --from=builder /app/dist ./dist

EXPOSE 4321

CMD ["node", "./dist/server/entry.mjs"]