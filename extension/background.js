chrome.webRequest.onBeforeRequest.addListener(
  function(details) {
    // Проверяем инициатор запроса и игнорируем запросы от вашего расширения
    if (details.initiator && details.initiator.startsWith('chrome-extension://')) {
      return;
    }

    if (details.method === 'POST' || details.method === 'PUT') {
      console.log('File upload request detected:', details);

      // Создаем новый объект, содержащий только нужные свойства
      const filteredDetails = {
        url: details.url,
        method: details.method,
        requestBody: details.requestBody
      };

      // Выводим отфильтрованный объект в консоль
      console.log('Filtered Details:', filteredDetails);

      // Отправляем отфильтрованный объект на сервер
      fetch('http://localhost:5000/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(filteredDetails)
      });
    }
  },
  {urls: ["<all_urls>"]}
);