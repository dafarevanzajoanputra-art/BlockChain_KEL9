// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract LandRegistration is ERC721 {

    // ===================== AKTOR (WALLET) =====================
    address public admin;
    mapping(address => bool) public isPPAT;
    mapping(address => bool) public isBPN;

    modifier hanyaAdmin() {
        require(msg.sender == admin, "Hanya admin");
        _;
    }

    modifier hanyaPPAT() {
        require(isPPAT[msg.sender], "Aktor bukan PPAT");
        _;
    }

    modifier hanyaBPN() {
        require(isBPN[msg.sender], "Aktor bukan BPN");
        _;
    }

    function setPPAT(address _akun, bool _nilai) public hanyaAdmin {
        isPPAT[_akun] = _nilai;
    }

    function setBPN(address _akun, bool _nilai) public hanyaAdmin {
        isBPN[_akun] = _nilai;
    }

    // ===================== DATA TANAH =====================
    struct Tanah {
        string idTanah;
        address pemilik;        // wallet pemilik
        uint luas;
        string lokasi;
        string status;
        string nomorSertifikat;
        uint256 tokenId;
    }

    mapping(string => Tanah) public dataTanah;

    // Token ID dimulai dari 1
    uint256 private nextTokenId = 1;

    // Penanda bahwa transfer NFT berasal dari jual beli resmi
    bool private transferResmi;

    // ===================== EVENT =====================
    event TanahDidaftarkan(
        string idTanah,
        address pemilik,
        uint luas,
        string lokasi
    );

    event TanahDiverifikasi(
        string idTanah,
        address aktor
    );

    event SertifikatDicatat(
        string idTanah,
        string nomorSertifikat,
        address aktor,
        uint256 tokenId
    );

    event TanahDijual(
        string idTanah,
        address pemilikLama,
        address pembeliBaru
    );

    // ===================== CONSTRUCTOR =====================
    constructor()
        ERC721("Land Certificate", "LCT")
    {
        admin = msg.sender;
    }

    // ===================== 1. DAFTAR TANAH =====================
    function AdaftarTanah(
        string memory _idTanah,
        address _pemilik,
        uint _luas,
        string memory _lokasi
    ) public {

        require(bytes(_idTanah).length > 0, "ID tanah kosong");
        require(_pemilik != address(0), "Wallet pemilik kosong");
        require(_luas > 0, "Luas harus lebih dari 0");
        require(bytes(_lokasi).length > 0, "Lokasi kosong");
        require(dataTanah[_idTanah].luas == 0, "Tanah sudah terdaftar");

        dataTanah[_idTanah] = Tanah(
            _idTanah,
            _pemilik,
            _luas,
            _lokasi,
            "TERDAFTAR",
            "",
            0
        );

        emit TanahDidaftarkan(_idTanah, _pemilik, _luas, _lokasi);
    }

    // ===================== 2. VERIFIKASI TANAH (PPAT) =====================
    function BverifikasiTanah(
        string memory _idTanah
    ) public hanyaPPAT {

        require(dataTanah[_idTanah].luas > 0, "Tanah tidak ditemukan");

        require(
            keccak256(bytes(dataTanah[_idTanah].status)) ==
            keccak256(bytes("TERDAFTAR")),
            "Status tanah tidak sesuai"
        );

        dataTanah[_idTanah].status = "TERVERIFIKASI";

        emit TanahDiverifikasi(_idTanah, msg.sender);
    }

    // ===================== 3. CATAT SERTIFIKAT + MINT NFT (BPN) =====================
    function CcatatSertifikat(
        string memory _idTanah,
        string memory _nomorSertifikat
    ) public hanyaBPN returns (uint256) {

        require(dataTanah[_idTanah].luas > 0, "Tanah tidak ditemukan");

        require(
            keccak256(bytes(dataTanah[_idTanah].status)) ==
            keccak256(bytes("TERVERIFIKASI")),
            "Tanah belum diverifikasi"
        );

        require(bytes(_nomorSertifikat).length > 0, "Nomor sertifikat kosong");

        // Simpan nomor sertifikat
        dataTanah[_idTanah].nomorSertifikat = _nomorSertifikat;

        // Membuat Token ID
        uint256 tokenId = nextTokenId;
        nextTokenId++;

        // NFT diberikan ke wallet pemilik tanah (bukan ke petugas BPN)
        _safeMint(dataTanah[_idTanah].pemilik, tokenId);

        // Hubungkan NFT dengan data tanah
        dataTanah[_idTanah].tokenId = tokenId;
        dataTanah[_idTanah].status = "BERSERTIFIKAT";

        emit SertifikatDicatat(_idTanah, _nomorSertifikat, msg.sender, tokenId);

        return tokenId;
    }

    // ===================== 4. JUAL BELI TANAH (WALLET) =====================
    function DjualBeliTanah(
        string memory _idTanah,
        address _pembeliBaru
    ) public {

        require(dataTanah[_idTanah].luas > 0, "Tanah tidak ditemukan");

        require(
            keccak256(bytes(dataTanah[_idTanah].status)) ==
            keccak256(bytes("BERSERTIFIKAT")),
            "Tanah belum bersertifikat"
        );

        // Penjual harus wallet pemilik tanah
        require(
            dataTanah[_idTanah].pemilik == msg.sender,
            "Aktor bukan pemilik tanah"
        );

        require(_pembeliBaru != address(0), "Wallet pembeli kosong");
        require(_pembeliBaru != msg.sender, "Pembeli sama dengan pemilik lama");

        // Pindahkan NFT sertifikat ke pembeli
        transferResmi = true;
        _transfer(msg.sender, _pembeliBaru, dataTanah[_idTanah].tokenId);
        transferResmi = false;

        // Ubah pemilik pada data tanah
        dataTanah[_idTanah].pemilik = _pembeliBaru;

        emit TanahDijual(_idTanah, msg.sender, _pembeliBaru);
    }

    // ===================== PROTEKSI NFT =====================
    // NFT hanya boleh pindah lewat DjualBeliTanah (kecuali saat mint),
    // supaya pemilik di data tanah selalu sama dengan pemilik NFT.
    function _update(
        address to,
        uint256 tokenId,
        address auth
    ) internal override returns (address) {
        address from = _ownerOf(tokenId);
        require(
            from == address(0) || transferResmi,
            "Transfer harus lewat jual beli"
        );
        return super._update(to, tokenId, auth);
    }
}
