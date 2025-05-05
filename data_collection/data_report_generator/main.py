import data_processing
import site_generator

if __name__ == '__main__':
    framework_data = data_processing.get_framework_data()
    site_generator.generate(framework_data)
