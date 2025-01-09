@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Perbedaan Magang dan Tokutei Ginou</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Magang dan Tokutei Ginou</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Content Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row">
            <div class="col-12 text-center mb-5">
                <h2 class="display-7">Perbedaan Program Magang dan Tokutei Ginou</h2>
            </div>
        </div>
        <div class="row g-4">
            <div class="col-12">
                <p class="mb-4">Magang dan Tokutei Ginou (技能実習生) adalah dua jenis program yang sering digunakan oleh pekerja asing di Jepang, tetapi ada beberapa perbedaan penting antara keduanya:</p>

                <div class="mb-5">
                    <h3 class="mb-4">1. Magang (Internship)</h3>
                    <ul class="list-unstyled ps-4">
                        <li class="mb-3"><strong>Tujuan:</strong> Program magang bertujuan untuk memberikan pelatihan dan pengalaman kerja kepada peserta untuk meningkatkan keterampilan mereka dalam bidang tertentu.</li>
                        <li class="mb-3"><strong>Durasi:</strong> Biasanya singkat, dapat berkisar antara beberapa bulan hingga satu atau dua tahun, tergantung pada programnya.</li>
                        <li class="mb-3"><strong>Status:</strong> Magang sering kali merupakan bagian dari pendidikan atau pelatihan profesional, dan peserta magang umumnya dianggap sebagai siswa atau trainee.</li>
                        <li class="mb-3"><strong>Pembayaran:</strong> Peserta magang mungkin dibayar atau tidak, tergantung pada program dan kebijakan perusahaan yang bersangkutan. Kadang-kadang mereka hanya menerima uang saku atau tunjangan.</li>
                        <li class="mb-3"><strong>Tujuan akhir:</strong> Program ini sering diikuti untuk mendapatkan pengalaman yang bisa digunakan untuk mencari pekerjaan di masa depan atau untuk pengembangan diri.</li>
                    </ul>
                </div>

                <div class="mb-5">
                    <h3 class="mb-4">2. Tokutei Ginou (技能実習生, Technical Intern Training Program)</h3>
                    <ul class="list-unstyled ps-4">
                        <li class="mb-3"><strong>Tujuan:</strong> Program Tokutei Ginou lebih difokuskan pada pelatihan kerja untuk membantu pengembangan keterampilan yang dibutuhkan di Jepang. Ini bertujuan untuk mentransfer keterampilan teknis dan pengetahuan kepada pekerja asing untuk meningkatkan kualitas pekerjaan mereka di negara asal.</li>
                        <li class="mb-3"><strong>Durasi:</strong> Durasi program Tokutei Ginou lebih lama dibandingkan magang, biasanya berlangsung antara 1 hingga 5 tahun.</li>
                        <li class="mb-3"><strong>Status:</strong> Peserta Tokutei Ginou biasanya bekerja penuh waktu di perusahaan yang terdaftar dalam program ini, dengan visa kerja khusus.</li>
                        <li class="mb-3"><strong>Pembayaran:</strong> Peserta dibayar oleh perusahaan yang mempekerjakan mereka, dengan gaji yang lebih besar dibandingkan dengan program magang.</li>
                        <li class="mb-3"><strong>Tujuan akhir:</strong> Program ini berfokus pada penerapan keterampilan teknis di tempat kerja, dengan harapan para peserta dapat membawa keterampilan yang diperoleh kembali ke negara asal mereka setelah selesai.</li>
                    </ul>
                </div>

                <div class="bg-light p-4 rounded">
                    <h3 class="mb-3">Kesimpulan</h3>
                    <ul class="mb-0">
                        <li class="mb-2">Magang lebih berfokus pada pembelajaran dan pengalaman, sering terkait dengan pendidikan atau pelatihan, dengan durasi lebih singkat.</li>
                        <li>Tokutei Ginou lebih berfokus pada pengembangan keterampilan teknis di tempat kerja, dengan tujuan untuk memajukan keterampilan pekerja asing dalam industri tertentu di Jepang, dan memiliki durasi yang lebih lama serta pembayaran yang lebih terjamin.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Content End -->

@endsection