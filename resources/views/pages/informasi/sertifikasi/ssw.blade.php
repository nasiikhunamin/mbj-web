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
        
    </div>
</div>
</div>

@endsection