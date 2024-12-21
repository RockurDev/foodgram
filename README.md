# Foodgram

**Foodgram** is an online platform for storing, organizing, and sharing favorite recipes. Developed as part of the Yandex Practicum course, this project was built independently from scratch to provide users with a seamless culinary experience.

## Features
- **Recipe Management**: Create, edit, and save your favorite recipes.
- **Shopping List**: Download ingredient lists for your selected recipes.
- **Favorites**: Add recipes to your favorites for quick access.
- **Sharing**: View and share recipes with friends and the community.
- **User Authentication**: Register and manage your account effortlessly.

## Technologies
Foodgram is built using a modern tech stack to ensure reliability, performance, and ease of use:
- **Python**
- **Django**
- **Django REST Framework (DRF)** — RESTful API for seamless client-server communication.
- **Djoser** — Simplified user authentication.
- **PostgreSQL** — Robust and scalable database backend.
- **Gunicorn** — WSGI server for handling application requests.
- **Nginx** — Web server for serving static files and acting as a reverse proxy.
- **GitHub Actions** — Automated CI/CD pipelines for testing and deployment.
- **Docker** — Containerization for consistent development and production environments.
- **Docker Compose** — Simplified orchestration with `docker-compose.yml` and `docker-compose.production.yml`.

## API Endpoints
Foodgram's API allows for comprehensive interaction with the platform. Below are examples of requests the server can handle.

### 1. List All Recipes
**Request**:
```http
GET /api/recipes/
```

**Response**:
```json
[
  {
    "id": 1,
    "name": "Spaghetti Carbonara",
    "author": "RockurDev",
    "ingredients": ["Spaghetti", "Eggs", "Parmesan", "Pancetta"],
    "is_favorite": true
  },
  {
    "id": 2,
    "name": "Chicken Curry",
    "author": "RockurDev",
    "ingredients": ["Chicken", "Curry Paste", "Coconut Milk"],
    "is_favorite": false
  }
]
```

### 2. Create a Recipe
**Request**:
```http
POST /api/recipes/
```
**Body**:
```json
{
  "ingredients": [
    {
      "id": 1,
      "amount": 2
    },
    {
      "id": 3,
      "amount": 150
    }
  ],
  "tags": [1, 2],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "Greek Salad",
  "text": "Mix all ingredients and season with olive oil.",
  "cooking_time": 10
}
```

**Response**:
```json
{
  "id": 3,
  "name": "Greek Salad",
  "ingredients": [
    {
      "id": 1,
      "name": "Tomatoes",
      "measurement_unit": "pcs",
      "amount": 2
    },
    {
      "id": 3,
      "name": "Feta Cheese",
      "measurement_unit": "grams",
      "amount": 150
    }
  ],
  "tags": [
    {
      "id": 1,
      "name": "Salad",
      "slug": "salad"
    },
    {
      "id": 2,
      "name": "Healthy",
      "slug": "healthy"
    }
  ],
  "image": "http://yourdomain.com/media/recipes/3/greek_salad.png",
  "text": "Mix all ingredients and season with olive oil.",
  "cooking_time": 10,
  "is_favorite": false
}
```

## Deployment
Foodgram can be deployed using Docker and Docker Compose. Below are the steps to set up the project locally or on a server.

### Prerequisites
- **Docker** installed on your machine.
- **Docker Compose** installed.

### Steps to Deploy

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/RockurDev/foodgram.git
   cd foodgram
   ```

2. **Set Up Environment Variables**:
   A bash script is available in the root directory of the project to create a `.env` file from a predefined template. Run the script as follows:
   ```bash
   bash create_env.sh
   ```
   After running the script, update the `.env` file with your specific configuration:
   ```env
   # Database configuration
   DB_HOST=<your-database-hostname> # e.g., 'db' for Docker
   DB_PORT=<your-database-port> # e.g., 5432
   POSTGRES_DB=<your-database-name> # e.g., 'foodgram'
   POSTGRES_USER=<your-database-user> # e.g., 'foodgram_user'
   POSTGRES_PASSWORD=<your-database-password> # e.g., 'MostSecuredPassword'

   # Django settings
   SECRET_KEY=<your-django-secret-key> # Generate using a secure method
   ALLOWED_HOSTS=<comma-separated-list-of-hosts> # e.g., 'localhost,example.com'
   DEBUG=<true-or-false> # Optional; Set to 'True' for development; 'False' for production
   ```

3. **Build and Run Containers**:
   For development:
   ```bash
   docker-compose up -d --build
   ```
   
   For production:
   ```bash
   docker-compose -f docker-compose.production.yml up -d --build
   ```

4. **Apply Migrations and Collect Static Files**:
   ```bash
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

5. **Access the Application**:
   Open `http://localhost/` or `http://yourdomain.com/` in your browser.

```

## Author
- **Daniil Tropin - RockurDev**  
  [GitHub](https://github.com/RockurDev/foodgram)

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

**Start cooking and sharing with Foodgram today!**
```