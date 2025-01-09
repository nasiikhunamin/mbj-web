@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Specified Skilled Worker (SSW)</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item"><a href="{{ route('informasi.sertifikasi') }}" class="text-white">Sertifikasi</a></li>
            <li class="breadcrumb-item active text-secondary">SSW</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container legal-gallery">
        <div class="row">
            <div class="col-12 text-center mb-5">
                <h2 class="display-7">Informasi Sertifikasi SSW</h2>
            </div>
        </div>
        <div class="row g-4">
            <div class="col-12">
                <h2 class="mb-4"><strong>Apa itu SSW?</strong></h2>
                <p class="mb-4">SSW (Specified Skilled Workers) adalah status izin tinggal yang diberikan kepada pekerja asing yang ingin bekerja di Jepang. SSW merupakan kebijakan keimigrasian yang diresmikan oleh pemerintah Jepang pada April 2019.</p>

                <h3 class="mb-3">Persyaratan SSW</h3>
                <p class="mb-4">Untuk mendapatkan status SSW, Anda harus memenuhi syarat-syarat berikut:</p>
                <ul class="mb-4 ps-4">
                    <li class="mb-2">Berusia minimal 18 tahun</li>
                    <li class="mb-2">Lulus Ujian Dasar Bahasa Jepang (JFT-Basic) atau Tes Kecakapan Bahasa Jepang (JLPT) Level N4</li>
                    <li class="mb-2">Lulus ujian keterampilan untuk bidang industri tertentu</li>
                    <li class="mb-2">Lulus tes wawancara untuk perusahaan Jepang yang Anda inginkan</li>
                </ul>

                <p class="mb-4">Setelah lulus, Anda dapat mencari pekerjaan di perusahaan Jepang melalui Sistem Informasi Pasar Tenaga Kerja (IPKOL) Kementerian Tenaga Kerja Indonesia.</p>
                
                <p class="mb-4">Pemegang visa SSW memiliki hak dan kewajiban yang sama dengan pekerja Jepang, termasuk gaji dan asuransi.</p>

                <h3 class="mb-3">Bidang Industri yang Tersedia</h3>
                <p class="mb-3">Beberapa bidang industri yang bisa dipilih untuk program SSW, di antaranya:</p>
                <ul class="mb-4 ps-4">
                    <li class="mb-2">Perawat lansia</li>
                    <li class="mb-2">Petugas kebersihan gedung</li>
                    <li class="mb-2">Industri pembuatan perangkat dan suku cadang mesin</li>
                    <li class="mb-2">Industri permesinan pabrik</li>
                    <li class="mb-2">Industri listrik, elektronik, dan informasi</li>
                    <li class="mb-2">Konstruksi</li>
                    <li class="mb-2">Industri pembuatan kapal dan permesinan kapal</li>
                    <li class="mb-2">Industri perawatan dan perbaikan kendaraan bermotor</li>
                    <li class="mb-2">Industri penerbangan</li>
                    <li class="mb-2">Industri perhotelan dan pariwisata</li>
                </ul>
            </div>
        </div>
    </div>
</div>

@endsection