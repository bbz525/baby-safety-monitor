FROM eclipse-temurin:21-jre
WORKDIR /app
COPY . /app
RUN ./mvnw -q -DskipTests package || mvn -q -DskipTests package
EXPOSE 8080
CMD ["java", "-jar", "target/backend-0.0.1-SNAPSHOT.jar"]
