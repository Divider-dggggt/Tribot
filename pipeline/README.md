## to run pipeline

### start
```
docker build -t pipeline-env .
docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env
docker exec -it pipeline-container bash
```

### run any
```
python baseline_classification_model/train.py
```

### stop
```
docker stop pipeline-container
docker rm pipeline-container
```

## train results

### baseline
```
Loaded 50 training examples
Label distribution: {2: 22, 3: 19, 4: 8, 1: 1}
Using non-stratified train/test split because at least one class has fewer than 2 samples.

Accuracy:
0.7

Classification report:
              precision    recall  f1-score   support

           2       0.60      1.00      0.75         3
           3       0.80      0.80      0.80         5
           4       0.00      0.00      0.00         2

    accuracy                           0.70        10
   macro avg       0.47      0.60      0.52        10
weighted avg       0.58      0.70      0.62        10
```