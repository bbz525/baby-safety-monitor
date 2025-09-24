FROM node:20-alpine
WORKDIR /app
COPY . /app
ENV VITE_API_BASE=http://localhost:8080
RUN npm ci || npm install
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
