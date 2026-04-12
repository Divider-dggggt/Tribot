FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["python", "baseline_classification_model/train.py"]
# Keep container alive instead of running a script
CMD ["tail", "-f", "/dev/null"]
# CMD ["bash"]