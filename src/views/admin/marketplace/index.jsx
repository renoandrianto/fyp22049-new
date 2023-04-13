import React from "react";

// Chakra imports
import {
  Box,
  Button,
  Flex,
  Grid,
  Link,
  Text,
  useColorModeValue,
  SimpleGrid,
  Heading
} from "@chakra-ui/react";

// Custom components
import DesBox from "views/admin/marketplace/components/DesBox";
// import TableTopCreators from "views/admin/marketplace/components/TableTopCreators";
// import HistoryItem from "views/admin/marketplace/components/HistoryItem";
// import NFT from "components/card/NFT";
// import Card from "components/card/Card.js";

// Assets
import Nft1 from "assets/img/nfts/Nft1.png";
import Nft2 from "assets/img/nfts/Nft2.png";
import Nft3 from "assets/img/nfts/Nft3.png";
import Nft4 from "assets/img/nfts/Nft4.png";
import Nft5 from "assets/img/nfts/Nft5.png";
import Nft6 from "assets/img/nfts/Nft6.png";
import Avatar1 from "assets/img/avatars/avatar1.png";
import Avatar2 from "assets/img/avatars/avatar2.png";
import Avatar3 from "assets/img/avatars/avatar3.png";
import Avatar4 from "assets/img/avatars/avatar4.png";
import tableDataTopCreators from "views/admin/marketplace/variables/tableDataTopCreators.json";
import { tableColumnsTopCreators } from "views/admin/marketplace/variables/tableColumnsTopCreators";

export default function Marketplace() {
  // Chakra Color Mode
  const textColor = useColorModeValue("secondaryGray.900", "white");
  const textColorBrand = useColorModeValue("brand.500", "white");
  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      {/* Main Fields */}
      <Flex direction={{ base: "column", xl: "row" }} mb="20px">
        <Box
          bg="gray.200"
          borderRadius="xl"
          boxShadow="lg"
          p="1rem"
          mr={{ base: 0, xl: "20px" }}
          mb={{ base: "20px", xl: 0 }}
          w={{ base: "100%", xl: "60%" }}
        >
          <Flex justify="center" align="center" direction="column">
            <Heading as="h2" size="lg" mb="1rem">
              Advantage Actor-Critic (A2C) Algorithm
            </Heading>
            <Text fontSize="md">
            The Advantage Actor-Critic (A2C) algorithm is a reinforcement learning algorithm that combines the benefits of both policy gradient and value function methods. A2C has been widely used in algorithmic trading as it can learn to make trading decisions based on market conditions and historical data.

A2C is particularly useful for algorithmic trading because it can handle continuous state and action spaces, which are commonly found in financial markets. This also allows real-time learning, increased flexibility to changing market conditions, improved trading performance and eventually better risk management.
              </Text>
          </Flex>
        </Box>
        <Box
          bg="gray.200"
          borderRadius="xl"
          boxShadow="lg"
          p="1rem"
          mr={{ base: 0, xl: "20px" }}
          mb={{ base: "20px", xl: 0 }}
          w={{ base: "100%", xl: "60%" }}
        >
          <Flex justify="center" align="center" direction="column">
            <Heading as="h2" size="lg" mb="1rem">
            Proximal Policy Optimization (PPO) Algorithm
            </Heading>
            <Text fontSize="md">
            The Proximal Policy Optimization (PPO) algorithm is again a reinforcement learning algorithm that can be used to develop trading strategies that adapt to changing market conditions and maximize returns while minimizing risk.

PPO is well-suited for algorithmic trading as it can handle large action and state spaces, which are common in financial markets.  This can lead to more efficient trading strategies and improved risk management.
              </Text>
          </Flex>
        </Box>
        <Box
          bg="gray.200"
          borderRadius="xl"
          boxShadow="lg"
          p="1rem"
          mr={{ base: 0, xl: "20px" }}
          mb={{ base: "20px", xl: 0 }}
          w={{ base: "100%", xl: "60%" }}
        >
          <Flex justify="center" align="center" direction="column">
            <Heading as="h2" size="lg" mb="1rem">
            Deep Deterministic Policy Gradient (DDPG) Algorithm
            </Heading>
            <Text fontSize="md">
            The Deep Deterministic Policy Gradient (DDPG) algorithm is a reinforcement learning algorithm that can handle large continuous action and can learn directly from raw data.

DDPG is particularly useful for us because it can learn to make trading decisions based on market conditions and historical data. Additionally, it can learn from high-dimensional data, such as price and volume data. 
              </Text>
          </Flex>
        </Box>
        <Box
          bg="gray.200"
          borderRadius="xl"
          boxShadow="lg"
          p="1rem"
          mb={{ base: "20px", xl: 0 }}
          w={{ base: "100%", xl: "60%" }}
        >
          <Flex justify="center" align="center" direction="column">
            <Heading as="h2" size="lg" mb="1rem">
            Twin Delayed Deep Deterministic (TD3) Algorithm
            </Heading>
            <Text fontSize="md">The Twin Delayed Deep Deterministic (TD3) algorithm is a reinforcement learning algorithm and is an extension of the Deep Deterministic Policy Gradient (DDPG) algorithm.
It  uses two critic networks to estimate the value function, which helps to reduce overestimation bias. TD3 has been shown to be effective in environments with noisy or delayed rewards, which are common in financial markets.  This means more a accurate trading strategy, and improved performance.</Text>
          </Flex>
        </Box>
      </Flex>
    </Box>
  );
}


