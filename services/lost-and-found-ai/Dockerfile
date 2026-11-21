FROM python:3.11-slim
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import torch; assert torch.version.cuda is None, 'CPU build required'"
COPY app ./app
ENV DEVICE=cpu
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
