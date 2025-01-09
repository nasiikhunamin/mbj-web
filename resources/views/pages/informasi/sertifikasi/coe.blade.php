@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Certificate of Eligibility (CoE)</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item"><a href="{{ route('informasi.sertifikasi') }}" class="text-white">Sertifikasi</a></li>
            <li class="breadcrumb-item active text-secondary">CoE</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Informasi Sertifikasi CoE</h2>
        </div>
    </div>
    <div class="row g-4">
        <div>
            <p class="has-text-align-left">Setiap orang yang akan bekerja di Jepang harus mempunyai CoE atau Certificate of Eligibility (CoE). Disebutkan CoE adalah sebuah dokumen yang menjadi syarat wajib ketika bekerja di Jepang. Apa sebenarnya itu CoE ?</p>
            <hr class="wp-block-separator">
                <h2 class="has-text-align-left wp-block-heading"><strong>Apa itu Certificate of Eligibility (CoE)?</strong></h2>
                <p class="has-text-align-left">Laman kemenaker.go,id menyebutkan bahwa CoE adalah dokumen yang dikeluarkan oleh Otoritas Imigrasi Jepang sebagai tanda bahwa orang asing boleh memasuki Jepang sesuai dengan tujuan/peruntukan yang diajukannya. Lebih lanjut disebutkan bahwa CoE ini hanya diperlukan jika orang asing tersebut berada di luar wilayah Jepang. Dokumen CoE ini diperlukan untuk mengajukan permohonan visa ke Perwakilan Jepang di Indonesia. Sementara itu untuk SSW, visa baru dapat dikeluarkan oleh Perwakilan Jepang di Indonesia jika CPMI telah memiliki e-ID yang dikeluarkan oleh BP2MI.</p>
                <p class="has-text-align-left">Certificate of Eligibility (COE) adalah sertifikasi yang diterbitkan oleh Ministry of Justice Jepang juga sebagai bukti bahwa seseorang tersebut layak untuk menetap di Jepang dalam jangka waktu tertentu. Sertifikasi ini bukan merupakan visa dan harus dibawa ke kedutaan Jepang di negara asal pendaftar untuk dapat diterbitkannya visa dalam paspor.</p>
                <p class="has-text-align-left">Khusus untuk visa bekerja, dokumen yang dibutuhkan terbit dari dua belah pihak. Baik dari pendaftar maupun dari kantor. Semua dokumen tidak dikembalikan sehingga harus menyiapkan lebih atau meminta izin kepada imigrasi untuk dikembalikan. Untuk proses penerbitan COE, semua dokumen harus dibawa ke kantor Imigrasi daerah di mana perusahaan tersebut berada.</p>
        </div>
    </div>
</div>
</div>

@endsection