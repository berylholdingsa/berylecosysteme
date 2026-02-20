FROM gradle:8.7-jdk17 AS build
WORKDIR /app
COPY build.gradle.kts settings.gradle.kts /app/
COPY src /app/src
RUN gradle installDist --no-daemon

FROM eclipse-temurin:17-jre
WORKDIR /opt/app
COPY --from=build /app/build/install/beryl-backend /opt/app
ENV PORT=8080
EXPOSE 8080
CMD ["/opt/app/bin/beryl-backend"]
