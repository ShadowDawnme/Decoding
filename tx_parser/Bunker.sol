// SPDX-License-Identifier: GPL-3.0
pragma solidity >= 0.4.16 < 0.9.0;

contract WrapUp {
    uint tranfer;
    string position;
    event InnerTx(address sender, address to, uint val);

    function setPosition(uint seter) public {
        tranfer = seter;
    }

    

}