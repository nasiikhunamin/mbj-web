@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Izin SO</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Izin SO</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h1 class="display-4">Izin SO MBJ Indonesia</h1>
            <p class="lead text-muted">Klik pada gambar untuk memperbesar</p>
        </div>
    </div>
    <div class="row">
      @php
          $documents = [
              asset('asset/img/izin-so-1.jpeg'),
              asset('asset/img/izin-so-2.jpeg'),
              asset('asset/img/izin-so-3.jpeg')
          ];
      @endphp

        @foreach($documents as $index => $document)
        <div class="col-md-4 col-sm-6 mb-4">
            <div class="gallery-item">
                <a href="{{ $document }}" data-lightbox="legal-docs" data-title="Legal Document {{ $index + 1 }}">
                    <img src="{{ $document }}" alt="Legal Document {{ $index + 1 }}" class="img-fluid">
                </a>
            </div>
        </div>
        @endforeach
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bs5-lightbox@1.8.3/dist/index.bundle.min.js"></script>

    

<!-- About End -->

@endsection

