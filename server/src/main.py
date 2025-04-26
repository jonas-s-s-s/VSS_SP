import control_logic
from dotenv import load_dotenv


def main():
    # Load environment variables from the config.env file
    load_dotenv(dotenv_path='../config.env')

    control_logic.initialize()


if __name__ == '__main__':
    main()
