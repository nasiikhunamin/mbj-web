@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Fasilitas</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Fasilitas</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Fasilitas Yang Kami Sediakan</h2>
        </div>
    </div>
    <div class="row g-4">
        @php
        $certifications = [
            [
                'id' => 'facility-1',
                'title' => 'Toilet',
                'image' => asset('asset/img/facilities-1.jpeg'),
            ],
            [
                'id' => 'facility-2',
                'title' => 'Dapur Bersama',
                'image' => asset('asset/img/facilities-2.jpeg'),
            ],
            [
                'id' => 'facility-3',
                'title' => 'Ruang Laundry',
                'image' => asset('asset/img/facilities-3.jpeg'),
            ],
            [
                'id' => 'facility-4',
                'title' => 'Ruang Kelas 1',
                'image' => asset('asset/img/facilities-4.jpeg'),
            ],
            [
                'id' => 'facility-5',
                'title' => 'Ruang Kelas 2',
                'image' => asset('asset/img/facilities-5.jpeg'),
            ],
            [
                'id' => 'facility-6',
                'title' => 'Ruang Asrama',
                'image' => asset('asset/img/facilities-6.jpeg'),
            ],
        ];
        @endphp

        @foreach($certifications as $certification)
        <div class="col-lg-4 col-md-6 col-sm-12">
            <div 
                class="card certification-card position-relative" 
                onclick="#"
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