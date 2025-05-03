FROM php:8.3.20-apache

WORKDIR /var/www/html

# Install system dependencies and extensions
RUN apt-get update && apt-get install -y \
    libpq-dev libzip-dev unzip curl git pkg-config \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && a2enmod rewrite \
    && sed -ri 's!DocumentRoot /var/www/html!DocumentRoot /var/www/html/public!g' /etc/apache2/sites-available/000-default.conf

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Copy only composer files first to optimize layer caching
COPY composer.json ./

# Install PHP dependencies
RUN composer install --no-dev --prefer-dist --optimize-autoloader --no-interaction --no-scripts

# Copy the rest of the application files
COPY . .

# Set permissions and generate app key
RUN chown -R www-data:www-data storage bootstrap/cache \
    && if [ -f artisan ]; then php artisan key:generate --ansi; fi

EXPOSE 80

ENV APP_ENV=production
ENV APP_DEBUG=false

CMD ["apache2-foreground"]
