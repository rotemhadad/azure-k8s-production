#service-a/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 81
CMD ["python", "app.py"]
