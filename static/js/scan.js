  async function run(){
    document.getElementById('loading').style.display = 'block';
    try {
      const response = await fetch('/start_processing');
      const data = await response.json();
      const alertDiv = document.getElementById('alert');

      document.getElementById('loading').style.display = 'none';

      alertDiv.textContent =' تم معالجة ${data.processed_count} صورة تحتوي على مخاطر.';

    } catch (error) {
      console.error('خطأ أثناء المعالجة:', error);
      document.getElementById('loading').style.display = 'none';
      document.getElementById('alert').textContent = 'حدث خطأ أثناء معالجة الصور.';
    }
  }