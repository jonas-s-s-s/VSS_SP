# --- Stage 1: Build vendor dependencies ---
FROM composer:2 AS vendor

WORKDIR /app

COPY . ./

# Install PHP dependencies
# If composer.lock is empty, fallback to composer update
RUN if [ ! -s composer.lock ]; then \
      composer update --no-dev --optimize-autoloader; \
    else \
      composer install --no-dev --prefer-dist --optimize-autoloader; \
    fi

# --- Stage 2: Production application image ---
FROM php:8.3.20-apache

# Set working directory
WORKDIR /var/www/html

# Install PHP extensions (Laravel needs these)
RUN docker-php-ext-install pdo pdo_mysql

# Enable Apache rewrite module
RUN a2enmod rewrite

# Change Apache's DocumentRoot to /public
RUN sed -ri 's!DocumentRoot /var/www/html!DocumentRoot /var/www/html/public!g' /etc/apache2/sites-available/000-default.conf

# Copy application code
COPY --from=vendor /app /var/www/html
COPY . /var/www/html

# Ensure writable permissions for storage and cache
RUN chown -R www-data:www-data storage bootstrap/cache

# Generate APP_KEY
RUN php artisan key:generate --ansi

# Expose port 80
EXPOSE 80

# Set environment variables for production
ENV APP_ENV=production
ENV APP_DEBUG=false

# Start Apache
CMD ["apache2-foreground"]
