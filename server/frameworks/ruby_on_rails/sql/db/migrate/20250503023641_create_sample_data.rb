class CreateSampleData < ActiveRecord::Migration[7.0]
  def change
    unless table_exists?(:sample_data)
      create_table :sample_data do |t|
        t.string :title, null: false
        t.timestamps
      end
    end
  end
end