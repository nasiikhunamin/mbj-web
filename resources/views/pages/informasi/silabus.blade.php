@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Apa Yang Dipelajari</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Program</a></li>
            <li class="breadcrumb-item active text-secondary">Kurikulum</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Content Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row">
            <div class="col-12 mb-5">
                <h2 class="text-center display-7 mb-4">Apa Saja yang Dipelajari di LPK Matahari Bulan Jepang Indonesia?</h2>
                <p class="text-center mb-5">Di LPK Matahari Bulan Jepang Indonesia, kami berkomitmen untuk membekali para peserta dengan keterampilan dan pengetahuan yang dibutuhkan untuk bekerja, belajar, dan sukses di Jepang. Program pelatihan kami dirancang secara khusus untuk memenuhi kebutuhan pasar kerja di Jepang, sambil memberikan fondasi budaya yang kuat.</p>
            </div>

            <div class="col-12">
                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">1. Pelatihan Bahasa Jepang</h3>
                        <p>Kami menyediakan pelatihan bahasa Jepang dari level dasar hingga lanjutan.</p>
                        <ul class="list-unstyled ps-3">
                            <li class="mb-3">🎯 <strong>Kurikulum N5-N4:</strong> Materi tata bahasa, kosakata, huruf Hiragana, Katakana, dan Kanji.</li>
                            <li class="mb-3">🎯 <strong>Percakapan Praktis:</strong> Fokus pada situasi sehari-hari, tempat kerja, dan komunikasi formal.</li>
                            <li>🎯 <strong>Simulasi Ujian JLPT:</strong> Persiapan untuk menghadapi tes sertifikasi kemampuan bahasa Jepang.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">2. Pemahaman Budaya dan Etika Kerja di Jepang</h3>
                        <ul class="list-unstyled ps-3">
                            <li class="mb-3">🎯 <strong>Budaya Jepang:</strong> Memahami kebiasaan, tradisi, dan norma sosial Jepang.</li>
                            <li class="mb-3">🎯 <strong>Etika Kerja:</strong> Pelatihan tentang disiplin, tanggung jawab, sopan santun, dan cara bekerja di lingkungan Jepang.</li>
                            <li>🎯 <strong>Pengalaman Praktis:</strong> Simulasi situasi di tempat kerja Jepang, seperti rapat, laporan, dan komunikasi antar kolega.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">3. Pelatihan Keterampilan Teknis</h3>
                        <p>Program ini menyesuaikan kebutuhan peserta yang akan bekerja di sektor-sektor tertentu di Jepang, seperti:</p>
                        <ul class="list-unstyled ps-3">
                            <li class="mb-3">🎯 <strong>Kesehatan:</strong> Pelatihan dasar untuk perawat dan caregiver (kaigo).</li>
                            <li class="mb-3">🎯 <strong>Manufaktur:</strong> Keterampilan teknis untuk industri pabrik dan teknologi.</li>
                            <li class="mb-3">🎯 <strong>Pertanian dan Perikanan:</strong> Pengenalan dan pelatihan praktik di bidang pertanian modern dan perikanan.</li>
                            <li>🎯 <strong>Jasa Layanan:</strong> Pelatihan untuk bekerja di sektor perhotelan, restoran, dan layanan pelanggan.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">4. Persiapan Keberangkatan ke Jepang</h3>
                        <ul class="list-unstyled ps-3">
                            <li class="mb-3">🎯 <strong>Pengurusan Dokumen:</strong> Bimbingan lengkap dalam pengurusan dokumen seperti visa dan kontrak kerja.</li>
                            <li class="mb-3">🎯 <strong>Orientasi Pra-Keberangkatan:</strong> Pelatihan tentang kehidupan di Jepang, manajemen keuangan, dan adaptasi lingkungan.</li>
                            <li>🎯 <strong>Simulasi Kehidupan:</strong> Menyiapkan peserta untuk beradaptasi dengan perbedaan budaya dan gaya hidup di Jepang.</li>
                        </ul>
                    </div>
                </div>

                <div class="card shadow-sm mb-5">
                    <div class="card-body">
                        <h3 class="card-title mb-4">5. Pendampingan dan Pengembangan Karir</h3>
                        <ul class="list-unstyled ps-3">
                            <li class="mb-3">🎯 <strong>Konsultasi Karir:</strong> Membantu peserta merancang karir mereka selama dan setelah program selesai.</li>
                            <li>🎯 <strong>Dukungan Alumni:</strong> Kami terus mendampingi alumni setelah program selesai untuk memastikan mereka sukses di Jepang.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Content End -->

@endsection