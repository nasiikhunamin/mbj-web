@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Sertifikasi</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Sertifikasi</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Program Sertifikasi Kami</h2>
            <p class="lead text-muted">Klik pada gambar untuk mengetahui lebih lanjut</p>
        </div>
    </div>
    <div class="row g-4">
        @php
        $certifications = [
            [
                'id' => 'coe',
                'title' => 'Certificate of Eligibility (CoE)',
                'image' => 'https://via.placeholder.com/600x400?text=Certificate+of+Eligibility',
                'route' => 'informasi.sertifikasi.coe'
            ],
            [
                'id' => 'jft',
                'title' => 'Japan Foundation Test for Basic Japanese',
                'image' => 'https://via.placeholder.com/600x400?text=JFT+Basic',
                'route' => 'informasi.sertifikasi.jft'
            ],
            [
                'id' => 'jlpt',
                'title' => 'Japanese Language Proficiency Test',
                'image' => 'https://via.placeholder.com/600x400?text=JLPT',
                'route' => 'informasi.sertifikasi.jlpt'
            ],
            [
                'id' => 'ssw',
                'title' => 'SSW',
                'image' => 'https://via.placeholder.com/600x400?text=SSW',
                'route' => 'informasi.sertifikasi.ssw'
            ]
        ];
        @endphp

        @foreach($certifications as $certification)
        <div class="col-lg-3 col-md-6 col-sm-12">
            <div 
                class="card certification-card position-relative" 
                onclick="window.location.href='{{ route($certification['route']) }}'"
            >
                <img 
                    src="{{ $certification['image'] }}" 
                    class="card-img-top" 
                    alt="{{ $certification['title'] }}"
                >
                <div class="certification-overlay">
                    <div class="certification-text">
                        {{ $certification['title'] }}
                    </div>
                </div>
            </div>
        </div>
        @endforeach
    </div>
</div>
</div>

@endsection