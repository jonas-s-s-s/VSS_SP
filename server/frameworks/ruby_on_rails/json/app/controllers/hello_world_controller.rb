class HelloWorldController < ApplicationController
  def index
    @data = {
      message: "Hello World",
      timestamp: Time.now.iso8601,
      randomNumber: rand(1000)
    }
  end
end
