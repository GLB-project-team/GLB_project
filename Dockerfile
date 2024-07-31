FROM python:3.11-slim

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get install -y google-chrome-stable

# ChromeDriver 설치
# RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
#     wget -N http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P ~/ && \
#     unzip ~/chromedriver_linux64.zip -d ~/ && \
#     rm ~/chromedriver_linux64.zip && \
#     mv -f ~/chromedriver /usr/local/bin/chromedriver && \
#     chown root:root /usr/local/bin/chromedriver && \
#     chmod 0755 /usr/local/bin/chromedriver
RUN CHROME_DRIVER_VERSION=114.0.5735.90 && \
    wget -N http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P /tmp && \
    unzip /tmp/chromedriver_linux64.zip -d /tmp && \
    rm /tmp/chromedriver_linux64.zip && \
    mv /tmp/chromedriver /usr/local/bin/chromedriver && \
    chmod 0755 /usr/local/bin/chromedriver

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
# CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
