/*
 * Интернет-магазин товаров для йоги -- клиентская логика (лр21).
 * Использует Fetch API для получения товаров из REST API (лр20)
 * и динамического рендеринга карточек на странице каталога.
 */

/**
 * Достаёт CSRF-токен Django из cookie (стандартный подход Django).
 * Используется при POST/PUT/DELETE запросах к API.
 */
function getCsrfToken() {
  const name = "csrftoken";
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + "=")) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

/** Показывает Bootstrap Toast с сообщением (успех/ошибка). */
function showToast(message, isError = false) {
  const container = document.getElementById("toast-container");
  if (!container) {
    // Если на странице нет контейнера для тостов -- просто выводим в консоль.
    console.log(message);
    return;
  }

  const toastEl = document.createElement("div");
  toastEl.className =
    "toast align-items-center border-0 " + (isError ? "text-bg-danger" : "toast-yoga");
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Закрыть"></button>
    </div>`;
  container.appendChild(toastEl);

  const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

/** Показывает спиннер загрузки внутри переданного контейнера. */
function showLoading(container) {
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner-border text-success" role="status">
        <span class="visually-hidden">Загрузка...</span>
      </div>
      <p class="mt-2">Загружаем товары...</p>
    </div>`;
}

/** Показывает сообщение об ошибке внутри переданного контейнера. */
function showError(container, message) {
  container.innerHTML = `
    <div class="error-state">
      <strong>Не удалось загрузить данные.</strong><br>
      ${message}
    </div>`;
}

/**
 * Строит карточку товара (Bootstrap card) на основе объекта товара из API.
 */
function buildProductCard(product) {
  const inStock = product.stock_quantity > 0;
  const photoBlock = product.photo
    ? `<img src="${product.photo}" class="card-img-top" alt="${escapeHtml(product.name)}">`
    : `<div class="product-card-img-placeholder">Фото скоро появится</div>`;

  const stockBadge = inStock
    ? `<span class="badge stock-badge in-stock">В наличии: ${product.stock_quantity} шт.</span>`
    : `<span class="badge stock-badge out-of-stock">Нет в наличии</span>`;

  const cartButton = inStock
    ? `<button class="btn btn-brand btn-sm" onclick="addToCart(${product.id})">В корзину</button>`
    : `<button class="btn btn-brand btn-sm" disabled>Нет в наличии</button>`;

  return `
    <div class="col-sm-6 col-md-4 col-lg-4 mb-4">
      <div class="card product-card h-100">
        ${photoBlock}
        <div class="card-body d-flex flex-column">
          <h5 class="card-title">${escapeHtml(product.name)}</h5>
          <p class="card-text text-muted small mb-1">${escapeHtml(product.category_name || "")}</p>
          <p class="price-tag mb-2">${product.price} BYN</p>
          <p class="mb-2">${stockBadge}</p>
          <div class="mt-auto d-flex justify-content-between align-items-center">
            <a href="/catalog/${product.id}/" class="btn btn-outline-brand btn-sm">Подробнее</a>
            ${cartButton}
          </div>
        </div>
      </div>
    </div>`;
}

/** Простая защита от XSS при вставке текста из API в innerHTML. */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

/**
 * Загружает товары из REST API (/api/products/) с учётом фильтров
 * и рендерит карточки в указанный контейнер.
 *
 * @param {string} containerId - id DOM-элемента, куда рендерить карточки
 * @param {Object} filters - { category, manufacturer, q }
 */
function loadProducts(containerId, filters = {}) {
  const container = document.getElementById(containerId);
  if (!container) return;

  showLoading(container);

  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.manufacturer) params.set("manufacturer", filters.manufacturer);

  const url = "/api/products/" + (params.toString() ? "?" + params.toString() : "");

  fetch(url, {
    method: "GET",
    credentials: "same-origin", // передаём сессионные cookies для SessionAuthentication
    headers: { Accept: "application/json" },
  })
    .then((response) => {
      if (response.status === 403 || response.status === 401) {
        throw new Error("Для просмотра каталога через API нужно войти в систему.");
      }
      if (!response.ok) {
        throw new Error("Сервер вернул ошибку " + response.status);
      }
      return response.json();
    })
    .then((data) => {
      let products = data.results || data;

      // Поиск по названию/описанию делаем на клиенте, т.к. это лр21
      // демонстрирует именно работу с Fetch API и динамический рендеринг.
      if (filters.q) {
        const q = filters.q.toLowerCase();
        products = products.filter(
          (p) =>
            p.name.toLowerCase().includes(q) ||
            (p.description || "").toLowerCase().includes(q)
        );
      }

      if (products.length === 0) {
        container.innerHTML = `<p class="text-muted">Товары не найдены. Попробуйте изменить фильтры.</p>`;
        return;
      }

      container.innerHTML = products.map(buildProductCard).join("");
    })
    .catch((error) => {
      showError(container, error.message);
    });
}

/**
 * Добавляет товар в корзину через серверный endpoint /cart/add/<id>/
 * (использует обычную Django-форму-эндпоинт из лр18, отправленную через fetch,
 * чтобы корзина оставалась согласованной с остальным сайтом).
 */
function addToCart(productId, quantity = 1) {
  const csrfToken = getCsrfToken();
  if (!csrfToken) {
    showToast("Войдите в систему, чтобы добавить товар в корзину.", true);
    return;
  }

  fetch(`/cart/add/${productId}/`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": csrfToken,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `quantity=${encodeURIComponent(quantity)}`,
  })
    .then((response) => {
      if (response.status === 403) {
        throw new Error("Войдите в систему, чтобы добавить товар в корзину.");
      }
      if (!response.ok && response.status !== 302) {
        throw new Error("Не удалось добавить товар в корзину.");
      }
      showToast("Товар добавлен в корзину!");
    })
    .catch((error) => {
      showToast(error.message, true);
    });
}

/** Применяет фильтры формы каталога и перезагружает карточки товаров. */
function applyCatalogFilters(event) {
  event.preventDefault();
  const form = event.target;
  const filters = {
    category: form.category.value,
    manufacturer: form.manufacturer.value,
    q: form.q.value.trim(),
  };
  loadProducts("product-grid", filters);
}
