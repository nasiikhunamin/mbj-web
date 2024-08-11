<!-- Navbar & Hero Start -->
<div class="container-fluid nav-bar p-0">
    <nav class="navbar navbar-expand-lg navbar-light bg-white px-4 px-lg-5 py-3 py-lg-0">
        <a href="" class="navbar-brand p-0">
            <h4 class="display-5 text-secondary m-0"><img src="{{ asset('asset/img/mjb-logo.png')}}" class="img-fluid" alt=""></h4>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse">
            <span class="fa fa-bars"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarCollapse">
            <div class="navbar-nav ms-auto py-0">
                <a href="{{ route('home') }}" class="nav-item nav-link active">Home</a>
                <div class="nav-item dropdown">
                    <a href="#" class="nav-link" data-bs-toggle="dropdown"><span class="dropdown-toggle">Profile</span></a>
                    <div class="dropdown-menu m-0">
                        <a href="{{ route('profile.tentang-perusahaan') }}" class="dropdown-item">Tentang Perusahaan</a>
                        <a href="{{ route('profile.legalitas') }}" class="dropdown-item">Legalitas</a>
                        <a href="{{ route('profile.izin-so') }}" class="dropdown-item">Izin SO</a>
                        <a href="{{ route('profile.struktur-organisasi') }}" class="dropdown-item">Struktur Organisasi</a>
                        <a href="{{ route('profile.lokasi-pendidikan') }}" class="dropdown-item">Lokasi Pendidikan</a>
                    </div>
                </div>
                <div class="nav-item dropdown">
                    <a href="#" class="nav-link" data-bs-toggle="dropdown"><span class="dropdown-toggle">Informasi</span></a>
                    <div class="dropdown-menu m-0">
                        <a href="{{ route('informasi.pendaftaran') }}" class="dropdown-item">Pendaftaran</a>
                        <a href="{{ route('informasi.prospek-karir') }}" class="dropdown-item">Prospek Karir</a>
                        <a href="{{ route('informasi.apa-yang-dipelajari') }}" class="dropdown-item">Apa yang Dipelajari</a>
                        <a href="{{ route('informasi.fasilitas') }}" class="dropdown-item">Fasilitas</a>
                        <a href="{{ route('informasi.sertifikasi') }}" class="dropdown-item">Sertifikasi</a>
                        <a href="{{ route('informasi.perbedaan-magang-tokutei-ginou') }}" class="dropdown-item">Perbedaan Magang & Tokutei Ginou</a>
                        <a href="{{ route('informasi.biaya-hidup-di-jepang') }}" class="dropdown-item">Biaya Hidup di Jepang</a>
                    </div>
                </div>
                <div class="nav-item dropdown">
                    <a href="#" class="nav-link" data-bs-toggle="dropdown"><span class="dropdown-toggle">Komunitas</span></a>
                    <div class="dropdown-menu m-0">
                        <a href="{{ route('komunitas.testimoni-alumni') }}" class="dropdown-item">Testimoni Alumni</a>
                        <a href="{{ route('komunitas.galeri') }}" class="dropdown-item">Galeri</a>
                        <a href="{{ route('komunitas.faq') }}" class="dropdown-item">FAQ</a>
                        <a href="{{ route('komunitas.proses-pindah-kerja') }}" class="dropdown-item">Proses Pindah Kerja</a>
                    </div>
                </div>
            </div>
            
            <a href="{{ route('daftar') }}" class="btn btn-primary border-secondary rounded-pill py-2 px-4 px-lg-3 mb-3 mb-md-3 mb-lg-0">Daftar Sekarang!</a>
        </div>
    </nav>
</div>
<!-- Navbar & Hero End -->