@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Biaya Hidup di Jepang</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Biaya Hidup</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Content Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row">
            <div class="col-12 mb-5">
                <h2 class="text-center display-7 mb-4">Biaya Hidup di Jepang: Apa yang Perlu Anda Ketahui?</h2>
                <p>Saat merencanakan perjalanan atau bekerja di Jepang, memahami biaya hidup adalah hal penting. Jepang dikenal sebagai salah satu negara dengan standar hidup tinggi, namun dengan perencanaan yang baik, Anda dapat mengelola pengeluaran secara efisien. Berikut adalah gambaran umum tentang biaya hidup di Jepang:</p>
            </div>

            <div class="col-12 mb-4">
                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">1. Tempat Tinggal</h3>
                        <ul class="list-unstyled">
                            <li class="mb-3"><strong>Asrama Pekerja/Magang:</strong> Banyak perusahaan menyediakan asrama dengan biaya terjangkau, mulai dari ¥10,000 hingga ¥30,000 per bulan.</li>
                            <li class="mb-3"><strong>Apartemen Pribadi:</strong> Jika menyewa apartemen, biaya bisa berkisar antara ¥40,000 hingga ¥100,000 per bulan, tergantung lokasi dan fasilitas. Kota besar seperti Tokyo biasanya lebih mahal dibandingkan daerah pedesaan.</li>
                            <li><strong>Biaya Tambahan:</strong> Jangan lupa memperhitungkan utilitas seperti listrik, gas, dan air, yang rata-rata memakan biaya ¥10,000 hingga ¥20,000 per bulan.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">2. Makan dan Minum</h3>
                        <ul class="list-unstyled">
                            <li class="mb-3"><strong>Masak Sendiri:</strong> Dengan memasak sendiri, Anda bisa menghemat pengeluaran. Rata-rata biaya bahan makanan sekitar ¥20,000 hingga ¥30,000 per bulan.</li>
                            <li class="mb-3"><strong>Makan di Luar:</strong> Harga makanan di restoran murah seperti kedai ramen atau donburi berkisar ¥500 hingga ¥1,000 per porsi. Jika makan di restoran kelas menengah, biayanya bisa mencapai ¥2,000 ke atas.</li>
                            <li><strong>Tips Hemat:</strong> Banyak supermarket menjual makanan dengan diskon besar di malam hari!</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">3. Transportasi</h3>
                        <ul class="list-unstyled">
                            <li class="mb-3"><strong>Kereta dan Bus:</strong> Jepang memiliki transportasi umum yang efisien. Biaya rata-rata naik kereta atau bus sekali jalan berkisar ¥200 hingga ¥400. Jika Anda sering bepergian, pertimbangkan membeli kartu bulanan (commuter pass), yang harganya mulai dari ¥5,000 tergantung rute.</li>
                            <li><strong>Sepeda:</strong> Banyak pekerja dan mahasiswa memilih sepeda untuk menghemat biaya transportasi. Sepeda bekas dapat dibeli dengan harga ¥5,000 hingga ¥10,000.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">4. Kesehatan dan Asuransi</h3>
                        <ul class="list-unstyled">
                            <li class="mb-3">Jepang mewajibkan semua penduduk untuk memiliki asuransi kesehatan nasional (National Health Insurance).</li>
                            <li>Biaya asuransi ini tergantung penghasilan, tetapi rata-rata berkisar ¥2,000 hingga ¥5,000 per bulan untuk pekerja baru. Dengan asuransi ini, Anda hanya perlu membayar 30% dari total biaya medis saat berobat.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">5. Hiburan dan Kebutuhan Lainnya</h3>
                        <ul class="list-unstyled">
                            <li class="mb-3"><strong>Hiburan:</strong> Tiket bioskop biasanya ¥1,800, sedangkan karaoke selama 1 jam berkisar ¥500 hingga ¥1,500.</li>
                            <li class="mb-3"><strong>Belanja Kebutuhan Sehari-hari:</strong> Biaya untuk kebutuhan seperti sabun, sampo, dan kebutuhan rumah tangga lain rata-rata ¥5,000 hingga ¥10,000 per bulan.</li>
                            <li><strong>Internet dan Ponsel:</strong> Paket ponsel atau internet bulanan biasanya sekitar ¥3,000 hingga ¥6,000, tergantung provider dan layanan yang dipilih.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">Tips Hemat Biaya Hidup di Jepang</h3>
                        <ul class="list-unstyled">
                            <li class="mb-2">🔹 <strong>Gunakan Diskon dan Promosi:</strong> Cari supermarket atau toko dengan diskon harian.</li>
                            <li class="mb-2">🔹 <strong>Pilih Asrama atau Share House:</strong> Berbagi tempat tinggal dengan orang lain bisa mengurangi biaya sewa.</li>
                            <li class="mb-2">🔹 <strong>Manfaatkan Transportasi Umum:</strong> Gunakan kartu transportasi seperti Suica atau Pasmo untuk kemudahan dan diskon perjalanan.</li>
                            <li>🔹 <strong>Bekerja Paruh Waktu:</strong> Banyak pekerja asing memanfaatkan peluang kerja paruh waktu (arubaito) untuk menambah penghasilan.</li>
                        </ul>
                    </div>
                </div>

                <div class="bg-light p-4 rounded">
                    <h3 class="mb-3">Kesimpulan</h3>
                    <p class="mb-3">Biaya hidup di Jepang bervariasi tergantung pada gaya hidup, lokasi, dan kebutuhan Anda. Dengan pengelolaan yang baik, Anda bisa menjalani kehidupan yang nyaman sekaligus hemat di Jepang.</p>
                    <p class="mb-0">Apakah Anda siap untuk memulai perjalanan hidup Anda di negeri Sakura?</p>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Content End -->

@endsection