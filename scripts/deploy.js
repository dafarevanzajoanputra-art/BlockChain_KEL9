
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    const [deployer] = await ethers.getSigners();

    console.log("Deploy menggunakan wallet:", deployer.address);

    // Baca alamat aktor dari actors.json
    const actorsPath = path.join(__dirname, "..", "actors.json");

    if (!fs.existsSync(actorsPath)) {
        throw new Error("File actors.json tidak ditemukan!");
    }

    const actors = JSON.parse(
        fs.readFileSync(actorsPath, "utf8")
    );

    if (!ethers.isAddress(actors.ppat)) {
        throw new Error("Alamat wallet PPAT tidak valid!");
    }

    if (!ethers.isAddress(actors.bpn)) {
        throw new Error("Alamat wallet BPN tidak valid!");
    }

    const ppatAddress = ethers.getAddress(actors.ppat);
    const bpnAddress = ethers.getAddress(actors.bpn);

    if (ppatAddress === bpnAddress) {
        throw new Error("Alamat wallet PPAT dan BPN tidak boleh sama!");
    }

    console.log("Wallet PPAT:", ppatAddress);
    console.log("Wallet BPN:", bpnAddress);

    // Deploy smart contract
    const LandRegistration = await ethers.getContractFactory(
        "LandRegistration"
    );

    const landRegistration = await LandRegistration.deploy();

    await landRegistration.waitForDeployment();

    const contractAddress = await landRegistration.getAddress();

    const network = await ethers.provider.getNetwork();

    console.log("\nLandRegistration berhasil di-deploy!");
    console.log("Alamat Smart Contract:", contractAddress);

    // Tetapkan role PPAT
    const txPPAT = await landRegistration.setPPAT(
        ppatAddress,
        true
    );

    await txPPAT.wait();

    console.log("Role PPAT berhasil ditetapkan!");

    // Tetapkan role BPN
    const txBPN = await landRegistration.setBPN(
        bpnAddress,
        true
    );

    await txBPN.wait();

    console.log("Role BPN berhasil ditetapkan!");

    // Simpan data deployment
    const deploymentData = {
        contractName: "LandRegistration",
        address: contractAddress,
        network: "localhost",
        chainId: Number(network.chainId),
        ppat: ppatAddress,
        bpn: bpnAddress
    };

    const deploymentPath = path.join(
        __dirname,
        "..",
        "deployment.json"
    );

    fs.writeFileSync(
        deploymentPath,
        JSON.stringify(deploymentData, null, 2)
    );

    console.log("\nDeployment selesai!");
    console.log("Alamat kontrak:", contractAddress);
    console.log("Alamat PPAT:", ppatAddress);
    console.log("Alamat BPN:", bpnAddress);
    console.log("Lokasi deployment.json:", deploymentPath);
}

main().catch((error) => {
    console.error("Deployment gagal:", error);
    process.exitCode = 1;
});
