FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

COPY gateway.js ./

EXPOSE 9000

CMD ["npm", "start"]