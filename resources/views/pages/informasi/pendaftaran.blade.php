@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Pendaftaran</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Pendaftaran</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
          <h2 class="display-7">Informasi dan Alur Pendaftaran Peserta</h2>
            <p class="lead text-muted">Berikut adalah langkah-langkah pelatihan di Jepang sebagai peserta praktek kerja magang</p>
        </div>
    </div>
    <div class="row align-items-center mb-4">
        <div class="col-md-6 mb-3 mb-md-0">
            <img src="{{ asset('asset/img/registration-flow-1.jpeg') }}" alt="Step 1" class="img-fluid rounded shadow">
        </div>
        <div class="col-md-6">
            <div class="admission-step">
                <h6 class="text-primary">Registration (Pendaftaran)</h6>
                <p class="text-muted">
                    Pada tahap ini, calon peserta magang akan melakukan pendaftaran di LPK Matahari Bulan Jepang Indonesia. Pendaftaran ini mencakup pengisian data pribadi dan informasi yang dibutuhkan untuk memulai proses seleksi dan persiapan keberangkatan.
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Interview dan Psikotes Pertama dengan LPK Matahari Bulan Jepang Indonesia</h6>
                <p class="text-muted">
                    Setelah pendaftaran, calon peserta akan menjalani proses wawancara awal dan psikotes untuk menilai kesiapan mental dan kecocokan dengan program magang. Proses ini bertujuan untuk memastikan bahwa peserta memiliki kemampuan yang diperlukan untuk bekerja di Jepang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Medical Check Up Pertama</h6>
                <p class="text-muted">
                    Tahap ini melibatkan pemeriksaan kesehatan awal untuk memastikan bahwa calon peserta dalam kondisi fisik yang baik dan tidak memiliki penyakit yang dapat menghalangi keberangkatan atau kelancaran magang di Jepang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Belajar Bahasa Jepang, Peraturan, dan Etika di Jepang</h6>
                <p class="text-muted">
                    Setelah lolos seleksi awal, peserta akan mengikuti pelatihan bahasa Jepang dasar serta pembelajaran mengenai peraturan dan etika yang berlaku di Jepang. Ini sangat penting untuk mempersiapkan peserta agar bisa beradaptasi dengan kehidupan dan budaya kerja di Jepang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Interview Rekrutmen dengan Perusahaan</h6>
                <p class="text-muted">
                    Pada tahap ini, peserta akan menghadapi wawancara langsung dengan perusahaan yang akan mempekerjakan mereka selama magang di Jepang. Proses ini bertujuan untuk menilai kesesuaian peserta dengan kebutuhan perusahaan serta untuk menentukan penempatan kerja yang sesuai
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Aplikasi Paspor, CoE dan Visa</h6>
                <p class="text-muted">
                    Setelah diterima oleh perusahaan, peserta akan mengajukan aplikasi paspor, Certificate of Eligibility (CoE), dan visa magang. Proses ini penting untuk memperoleh izin resmi untuk tinggal dan bekerja di Jepang selama periode magang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Medical Check Up Sebelum Keberangkatan</h6>
                <p class="text-muted">
                    Sebelum keberangkatan, peserta akan menjalani pemeriksaan kesehatan lanjutan untuk memastikan kondisi fisik yang prima. Hal ini juga untuk memenuhi persyaratan kesehatan yang ditetapkan oleh pihak imigrasi Jepang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Orientasi Sebelum Keberangkatan & Berangkat</h6>
                <p class="text-muted">
                    Pada tahap ini, peserta akan mendapatkan orientasi mengenai kehidupan dan pekerjaan di Jepang. Orientasi ini juga mencakup informasi penting terkait keberangkatan, seperti penerbangan, kedatangan di Jepang, dan pengaturan tempat tinggal. Setelah orientasi, peserta akan diberangkatkan ke Jepang
                </p>
            </div>
            <div class="admission-step">
                <h6 class="text-primary">Memulai Magang Teknis di Jepang</h6>
                <p class="text-muted">
                    Setelah tiba di Jepang, peserta akan memulai program magang teknis sesuai dengan bidang yang telah ditentukan. Mereka akan bekerja di perusahaan yang sudah ditempatkan dan memulai pengalaman magang untuk memperdalam keterampilan teknis dan mendapatkan pengalaman kerja di Jepang
                </p>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-12 text-center mt-4">
            <a href="https://api.whatsapp.com/send?phone=6285283972464&amp;text=Halo, saya mau informasi lebih lanjut tentang MBJ Indonesia. || Hello, I want to know more about MBJ Indonesia." target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-lg pulse-animation">
                Daftar Sekarang!
                <i class="bi bi-arrow-right-circle ms-2"></i>
            </a>
        </div>
    </div>
    
</div>
</div>    

<!-- About End -->

@endsection

