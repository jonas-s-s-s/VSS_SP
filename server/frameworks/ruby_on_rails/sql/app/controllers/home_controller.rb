class HomeController < ApplicationController
  def index
    @sample_data = SampleData.all
  end
end