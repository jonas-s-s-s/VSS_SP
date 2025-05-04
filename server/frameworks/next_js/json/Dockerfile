# Build the app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

# Make sure that copy command doesn't throw exception if any of those weren't created by the build step
RUN mkdir -p /app/.next /app/public /app/node_modules

# Run the app
FROM node:20-alpine

WORKDIR /app

# Only copy needed files
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

ENV NODE_ENV production

# Start production server
CMD ["npm", "run", "start"]
