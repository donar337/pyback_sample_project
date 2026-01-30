# pyback_sample_project

1. Настраиваем окружение:

    Нужно создать .env файл в корне проекта, пример в [.env.example](.env.example), можно просто скопировать его.

2. Поднимаем проект:

    ```bash
    docker compose up -d
    ```

3. Убедиться в работоспособности:

    3.1. Отправляем запрос на создание заказа

        ```shell
        $body = '{"customer_id":"550e8400-e29b-41d4-a716-446655440000","items":[{"product_id":"660e8400-e29b-41d4-a716-446655440000","quantity":2,"price":"99.99"}]}'; $response = Invoke-WebRequest -Uri http://localhost:8000/orders/ -Method POST -Body $body -ContentType "application/json" -UseBasicParsing; Write-Host "Status: $($response.StatusCode)"; $response.Content
        ```

        Должно быть 201 и должно вернуть id (убеждаемся что база работает)

    3.2. Запрос на получение того же заказа

        ```shell
        $orderId = "<order_id>"; Invoke-WebRequest -Uri "http://localhost:8000/orders/$orderId" -UseBasicParsing | Select-Object -ExpandProperty Content
        ```
        Убеждаемся что статус изменился на PROCESSED и updated_at изменился, значит брокер сообщений и consumer работают
    
    3.3. Можно также убедиться в работоспособности сбора метрик:

        ```shell
        Write-Host "=== СЦЕНАРИЙ 6: Проверка метрик Prometheus ==="; Write-Host "`nПроверка метрик после создания заказов:"; $metrics = (Invoke-WebRequest -Uri http://localhost:8000/metrics/ -UseBasicParsing).Content; $ordersCount = ([regex]::Matches($metrics, 'http_requests_total\{method="POST",path="/orders/"\}')).Count; Write-Host "POST /orders/ запросов: $ordersCount"; $getOrdersCount = ([regex]::Matches($metrics, 'http_requests_total\{method="GET",path="/orders/')).Count; Write-Host "GET /orders/ запросов: $getOrdersCount"; Write-Host "`nМетрики http_requests_total для /orders/:"; ($metrics -split "`n" | Select-String 'http_requests_total.*orders' | Select-Object -First 10) -join "`n"
        ```

4. Тесты автоматизированы через CI, покрытие 95%, покрытие видно в соответствующем артефакте пайплайна.